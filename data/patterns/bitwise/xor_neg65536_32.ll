define i32 @pattern_xor_neg65536_32(i32 %x) {
entry:
  %result = xor i32 %x, -65536
  ret i32 %result
}
