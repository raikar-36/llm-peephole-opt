define i32 @pattern_xor_neg2_32(i32 %x) {
entry:
  %result = xor i32 %x, -2
  ret i32 %result
}
