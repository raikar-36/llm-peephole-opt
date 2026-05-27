define dso_local i32 @f_b026(i32 noundef %0) local_unnamed_addr #0 {
  %2 = shl i32 %0, 24
  %3 = ashr exact i32 %2, 24
  ret i32 %3
}
