define i32 @pattern_xor_0_32(i32 %x) {
entry:
  %result = xor i32 %x, 0
  ret i32 %result
}
