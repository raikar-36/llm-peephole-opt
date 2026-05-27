define i64 @pattern_mul_128_64(i64 %x) {
entry:
  %result = mul i64 %x, 128
  ret i64 %result
}
