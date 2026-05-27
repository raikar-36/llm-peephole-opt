define i64 @pattern_xor_1_64(i64 %x) {
entry:
  %result = xor i64 %x, 1
  ret i64 %result
}
