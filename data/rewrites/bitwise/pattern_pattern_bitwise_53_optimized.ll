define i32 @pattern_bitwise_53(i32 %x, i32 %y) {
entry:
  %1 = xor i32 %y, 18
  %2 = and i32 %x, %1
  ret i32 %2
}