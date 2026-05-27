define dso_local noundef i32 @f_c013(i32 noundef %0) local_unnamed_addr #0 {
  %2 = ashr i32 %0, 31
  %3 = icmp ne i32 %0, 0
  %4 = zext i1 %3 to i32
  %5 = or i32 %2, %4
  ret i32 %5
}
