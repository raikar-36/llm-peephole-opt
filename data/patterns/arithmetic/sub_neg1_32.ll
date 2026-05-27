define i32 @pattern_sub_neg1_32(i32 %x) {
entry:
  %result = sub i32 %x, -1
  ret i32 %result
}
