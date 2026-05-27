define i64 @pattern_mul_neg1_64(i64 %x) {
entry:
  %result = mul i64 %x, -1
  ret i64 %result
}
