define dso_local noundef i32 @f_sp011(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = icmp ne i32 %0, 0
  %4 = icmp ne i32 %1, 0
  %5 = and i1 %3, %4
  %6 = zext i1 %5 to i32
  ret i32 %6
}
