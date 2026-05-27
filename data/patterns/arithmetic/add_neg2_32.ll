define i32 @pattern_add_neg2_32(i32 %x) {
entry:
  %result = add i32 %x, -2
  ret i32 %result
}
