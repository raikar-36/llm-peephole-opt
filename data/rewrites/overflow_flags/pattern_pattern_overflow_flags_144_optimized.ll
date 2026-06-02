define i32 @pattern_overflow_flags_144(i32 %x, i32 %y) {
entry:
  %1 = add nsw i32 %y, 4
  ret i32 %1
}