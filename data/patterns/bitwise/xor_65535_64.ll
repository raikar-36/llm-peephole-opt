define i64 @pattern_xor_65535_64(i64 %x) {
entry:
  %result = xor i64 %x, 65535
  ret i64 %result
}
