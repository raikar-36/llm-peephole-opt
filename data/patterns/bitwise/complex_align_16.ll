define dso_local noundef i32 @f_x003(i32 noundef %0) local_unnamed_addr #0 {
  %2 = add i32 %0, 15
  %3 = and i32 %2, -16
  ret i32 %3
}
