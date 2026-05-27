define dso_local noundef i32 @f_sp009(i32 noundef %0) local_unnamed_addr #0 {
  %2 = tail call i32 @llvm.abs.i32(i32 %0, i1 false)
  %3 = sub i32 0, %2
  ret i32 %3
}
