define i1 @pattern_comparison_91(i32 %x, i32 %y) {
entry:
  %1 = icmp eq i32 %x, %y
  ret i1 %1
}