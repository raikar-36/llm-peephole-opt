define i32 @pattern_xor_2_32(i32 %x) {
entry:
  %result = xor i32 %x, 2
  ret i32 %result
}
