define dso_local i32 @f_c009(i32 noundef %0) local_unnamed_addr #0 {
  %2 = tail call i32 @llvm.abs.i32(i32 %0, i1 true)
  ret i32 %2
}
