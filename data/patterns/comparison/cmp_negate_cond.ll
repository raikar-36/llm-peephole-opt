define dso_local noundef i32 @f_c017(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = icmp sgt i32 %0, %1
  %4 = zext i1 %3 to i32
  ret i32 %4
}
