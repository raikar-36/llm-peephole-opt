define dso_local noundef i32 @f_sp005(i32 noundef %0, i32 noundef %1, i32 noundef %2) local_unnamed_addr #0 {
  %4 = icmp eq i32 %0, 0
  %5 = select i1 %4, i32 %2, i32 %1
  ret i32 %5
}
