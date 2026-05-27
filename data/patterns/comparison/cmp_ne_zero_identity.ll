define dso_local noundef i32 @f_c008(i32 noundef %0) local_unnamed_addr #0 {
  %2 = icmp ne i32 %0, 0
  %3 = zext i1 %2 to i32
  ret i32 %3
}
