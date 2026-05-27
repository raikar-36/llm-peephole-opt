define dso_local noundef i32 @f_sp001(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = icmp eq i32 %0, 0
  %4 = select i1 %3, i32 %1, i32 %0
  ret i32 %4
}
