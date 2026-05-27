define dso_local noundef i32 @f_b017(i32 noundef %0) local_unnamed_addr #0 {
  %2 = lshr i32 %0, 3
  %3 = and i32 %2, 1
  ret i32 %3
}
