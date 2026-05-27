define i64 @pattern_mul_neg65536_64(i64 %x) {
entry:
  %result = mul i64 %x, -65536
  ret i64 %result
}
