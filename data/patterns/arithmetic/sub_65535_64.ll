define i64 @pattern_sub_65535_64(i64 %x) {
entry:
  %result = sub i64 %x, 65535
  ret i64 %result
}
