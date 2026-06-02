define i32 @pattern_bitwise_48(i32 %x, i32 %y) {
entry:
  %1 = xor i32 13, %y
  %2 = and i32 %x, %1
  ret i32 %2
}