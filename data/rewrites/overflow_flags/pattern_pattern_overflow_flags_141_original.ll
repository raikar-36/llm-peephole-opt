define i32 @pattern_overflow_flags_141(i32 %x, i32 %y) {
entry:
  %0 = add nsw i32 %x, %y
  %1 = add nsw i32 %0, 1
  %2 = sub nsw i32 %1, %x
  ret i32 %2
}