define i1 @pattern_comparison_109(i32 %x, i32 %y) {
entry:
  %1 = icmp eq i32 %x, %y
  ret i1 %1
}