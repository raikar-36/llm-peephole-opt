define dso_local noundef i32 @f_shl15(i32 noundef %0) local_unnamed_addr #0 {
  %2 = and i32 %0, 131071
  ret i32 %2
}
