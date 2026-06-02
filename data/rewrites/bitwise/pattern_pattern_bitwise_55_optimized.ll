define i32 @pattern_bitwise_55(i32 %x, i32 %y) {
entry:
  %1 = xor i32 20, %y
  %2 = and i32 %x, %1
  ret i32 %2
}