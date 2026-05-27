define i64 @pattern_xor_neg65536_64(i64 %x) {
entry:
  %result = xor i64 %x, -65536
  ret i64 %result
}
