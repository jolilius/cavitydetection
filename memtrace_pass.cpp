// memtrace_pass.cpp — LLVM new-pass-manager plugin (LLVM 15+, opaque pointers)
//
// Instruments every load and store in GaussBlur, ComputeEdges, Reverse, and
// DetectRoots with calls to __memtrace_load / __memtrace_store defined in
// memtrace_runtime.c.
//
// Prototype injected into the module:
//   void __memtrace_load (void *addr, uint64_t size, const char *func, int line)
//   void __memtrace_store(void *addr, uint64_t size, const char *func, int line)

#include "llvm/IR/DataLayout.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Plugins/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"

#include <string>
#include <vector>

using namespace llvm;

// Instrument every function in the module EXCEPT runtime callbacks and
// LLVM intrinsics.  This allows whole-program restructuring: the pass is run
// only on the evolved bitcode (before linking with the harness), so harness
// helper functions are never instrumented.
static bool shouldInstrument(const Function &F)
{
    StringRef name = F.getName();
    // Avoid instrumenting our own callbacks (would cause infinite recursion)
    if (name.starts_with("__memtrace_")) return false;
    if (name.starts_with("memtrace_"))   return false;
    // Skip LLVM intrinsics
    if (name.starts_with("llvm."))       return false;
    return true;
}

namespace {

struct MemTracePass : PassInfoMixin<MemTracePass> {

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
        LLVMContext &Ctx   = M.getContext();
        const DataLayout &DL = M.getDataLayout();

        // All pointers are opaque `ptr` in LLVM 15+
        Type *VoidTy   = Type::getVoidTy(Ctx);
        Type *PtrTy    = PointerType::getUnqual(Ctx);
        Type *Int64Ty  = Type::getInt64Ty(Ctx);
        Type *Int32Ty  = Type::getInt32Ty(Ctx);

        FunctionType *TraceFT = FunctionType::get(
            VoidTy, {PtrTy, Int64Ty, PtrTy, Int32Ty}, /*isVarArg=*/false);

        FunctionCallee LoadFn  = M.getOrInsertFunction("__memtrace_load",  TraceFT);
        FunctionCallee StoreFn = M.getOrInsertFunction("__memtrace_store", TraceFT);

        bool Changed = false;

        for (Function &F : M) {
            if (F.isDeclaration()) continue;
            if (!shouldInstrument(F)) continue;

            IRBuilder<> IRB(Ctx);

            // Create a global string constant for the function name once per function
            // (CreateGlobalString is the non-deprecated form in LLVM 15+; it returns
            //  a GlobalVariable* which decays to ptr in opaque-pointer mode)
            Constant *FuncNamePtr = IRB.CreateGlobalString(
                F.getName(), ".memtrace." + F.getName().str(), 0, &M);

            // Collect instructions first to avoid iterator invalidation
            std::vector<Instruction *> Worklist;
            for (auto &BB : F)
                for (auto &I : BB)
                    if (isa<LoadInst>(I) || isa<StoreInst>(I))
                        Worklist.push_back(&I);

            for (Instruction *I : Worklist) {
                unsigned Line = 0;
                if (const DILocation *Loc = I->getDebugLoc())
                    Line = Loc->getLine();

                Value *Ptr   = nullptr;
                uint64_t Sz  = 0;
                bool IsLoad  = false;

                if (auto *LI = dyn_cast<LoadInst>(I)) {
                    Ptr    = LI->getPointerOperand();
                    Sz     = DL.getTypeStoreSize(LI->getType());
                    IsLoad = true;
                } else if (auto *SI = dyn_cast<StoreInst>(I)) {
                    Ptr    = SI->getPointerOperand();
                    Sz     = DL.getTypeStoreSize(SI->getValueOperand()->getType());
                    IsLoad = false;
                }

                IRB.SetInsertPoint(I);
                IRB.CreateCall(IsLoad ? LoadFn : StoreFn, {
                    Ptr,
                    ConstantInt::get(Int64Ty, Sz),
                    FuncNamePtr,
                    ConstantInt::get(Int32Ty, Line)
                });
                Changed = true;
            }
        }

        return Changed ? PreservedAnalyses::none() : PreservedAnalyses::all();
    }

    // Required so the pass is not skipped when optimisations are off
    static bool isRequired() { return true; }
};

} // namespace

// Plugin entry-point — called by opt when the .dylib is loaded
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        LLVM_PLUGIN_API_VERSION, "memtrace", LLVM_VERSION_STRING,
        [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &MPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                    if (Name == "memtrace") {
                        MPM.addPass(MemTracePass());
                        return true;
                    }
                    return false;
                });
        }
    };
}
