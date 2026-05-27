define i32 @pattern_xor_128_32(i32 %x) {
entry:
  %result = xor i32 %x, 128
  ret i32 %result
}
