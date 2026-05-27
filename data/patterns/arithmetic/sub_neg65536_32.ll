define i32 @pattern_sub_neg65536_32(i32 %x) {
entry:
  %result = sub i32 %x, -65536
  ret i32 %result
}
