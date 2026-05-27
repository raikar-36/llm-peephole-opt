define dso_local noundef i32 @f_sp012(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = or i32 %1, %0
  %4 = icmp ne i32 %3, 0
  %5 = zext i1 %4 to i32
  ret i32 %5
}
