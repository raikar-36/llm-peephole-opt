define i1 @pattern_comparison_103(i32 %x, i32 %y) {
entry:
  %0 = add i32 %x, 13
  %1 = add i32 %y, 13
  %2 = icmp eq i32 %0, %1
  ret i1 %2
}