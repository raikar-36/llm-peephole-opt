define i32 @pattern_add_neg65536_32(i32 %x) {
entry:
  %result = add i32 %x, -65536
  ret i32 %result
}
