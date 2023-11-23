#ifndef DEBLOAT_PASS_H
#define DEBLOAT_PASS_H

#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

class DebloatPass : public llvm::PassInfoMixin<DebloatPass> {
public:
  llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &);
  bool runOnModule(llvm::Module &M);

  static bool isRequired() { return true; }
};

#endif //DEBLOAT_PASS_H
