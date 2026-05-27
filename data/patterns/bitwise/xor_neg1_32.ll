define i32 @pattern_xor_neg1_32(i32 %x) {
entry:
  %result = xor i32 %x, -1
  ret i32 %result
}
