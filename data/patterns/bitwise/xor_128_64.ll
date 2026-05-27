define i64 @pattern_xor_128_64(i64 %x) {
entry:
  %result = xor i64 %x, 128
  ret i64 %result
}
