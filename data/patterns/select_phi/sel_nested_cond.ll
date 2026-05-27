define dso_local noundef i32 @f_sp006(i32 noundef %0) local_unnamed_addr #0 {
  %2 = tail call i32 @llvm.smax.i32(i32 %0, i32 0)
  ret i32 %2
}
