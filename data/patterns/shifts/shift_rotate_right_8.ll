define dso_local noundef i32 @f_s010(i32 noundef %0) local_unnamed_addr #0 {
  %2 = tail call i32 @llvm.fshl.i32(i32 %0, i32 %0, i32 24)
  ret i32 %2
}
