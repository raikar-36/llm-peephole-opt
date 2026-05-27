define i64 @pattern_sub_neg65536_64(i64 %x) {
entry:
  %result = sub i64 %x, -65536
  ret i64 %result
}
