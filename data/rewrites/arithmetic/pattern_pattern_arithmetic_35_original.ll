define i32 @pattern_arithmetic_35(i32 %x, i32 %y) {
entry:
  %0 = add i32 %x, %y
  %1 = add i32 %0, 35
  %2 = sub i32 %1, %x
  ret i32 %2
}