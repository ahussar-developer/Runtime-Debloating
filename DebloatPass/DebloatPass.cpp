#include "DebloatPass.h"

#include "llvm/Transforms/IPO/SCCP.h"

#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/raw_ostream.h"

using namespace llvm;

PreservedAnalyses DebloatPass::run(llvm::Module &M, llvm::ModuleAnalysisManager &){
  bool changed = runOnModule(M);
	return (changed ? llvm::PreservedAnalyses::none()
                  : llvm::PreservedAnalyses::all());

}
bool DebloatPass::runOnModule(llvm::Module &M){
	for (Function &F : M){
	    errs() << "Function: " << F.getName().str() << "\n";
	}
  return false;
}


// This is the core interface for pass plugins. It guarantees that 'opt' will
// be able to recognize HelloWorld when added to the pass pipeline on the
// command line, i.e. via '-passes=hello-world'
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "DebloatPass", LLVM_VERSION_STRING,
          [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &MPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "debloat") {
                    MPM.addPass(DebloatPass());
                    return true;
                  }
                  return false;
                });
          }};
}
