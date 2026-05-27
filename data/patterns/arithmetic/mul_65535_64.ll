define i64 @pattern_mul_65535_64(i64 %x) {
entry:
  %result = mul i64 %x, 65535
  ret i64 %result
}
