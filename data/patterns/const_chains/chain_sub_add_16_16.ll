define i32 @chain_sub_add_16_16(i32 %x) {
entry:
  %tmp = sub i32 %x, 16
  %result = add i32 %tmp, 16
  ret i32 %result
}
