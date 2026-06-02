define i32 @pattern_bitwise_44(i32 %x, i32 %y) {
entry:
  %0 = and i32 %x, 9
  %1 = and i32 %x, %y
  %2 = xor i32 %0, %1
  ret i32 %2
}