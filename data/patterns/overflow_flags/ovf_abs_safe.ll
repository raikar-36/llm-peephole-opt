define dso_local i32 @f_o007(i32 noundef %0) local_unnamed_addr #0 {
  %2 = icmp ugt i32 %0, -2147483648
  %3 = sub nsw i32 0, %0
  %4 = select i1 %2, i32 %3, i32 %0
  ret i32 %4
}
