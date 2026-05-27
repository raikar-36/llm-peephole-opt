define i64 @pattern_sub_255_64(i64 %x) {
entry:
  %result = sub i64 %x, 255
  ret i64 %result
}
