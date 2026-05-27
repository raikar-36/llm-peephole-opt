define dso_local noundef i32 @f_x002(i32 noundef %0) local_unnamed_addr #0 {
  %2 = add i32 %0, 3
  %3 = and i32 %2, -4
  ret i32 %3
}
