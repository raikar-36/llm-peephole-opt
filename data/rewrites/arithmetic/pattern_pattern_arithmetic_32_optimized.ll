define i32 @pattern_arithmetic_32(i32 %x, i32 %y) {
entry:
  %1 = add i32 %y, 32
  ret i32 %1
}